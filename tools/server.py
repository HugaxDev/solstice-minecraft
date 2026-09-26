#!/usr/bin/env python3
"""Serveur Fabric headless local (127.0.0.1 uniquement) + client RCON minimal.

Usage en module :
    with Server(dir, world="Fragments", mods=[...]) as srv:
        srv.rcon("datapack list")
Le serveur est toujours arrêté à la sortie (stop RCON, puis kill si nécessaire).
"""
import atexit
import os
import re
import shutil
import signal
import socket
import struct
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import CACHE, java_bin  # noqa: E402

RCON_PORT = 25585
GAME_PORT = 25575
RCON_PASS = "solstice-local-test"

VOID_GEN = ('{"biome":"minecraft:the_void","layers":[{"block":"minecraft:air","height":1}],'
            '"features":false,"lakes":false,"structure_overrides":[]}')


class Rcon:
    def __init__(self, host, port, password):
        self.sock = socket.create_connection((host, port), timeout=30)
        self.req = 0
        self._send(3, password)
        rid, _, _ = self._recv()
        if rid == -1:
            raise RuntimeError("RCON : authentification refusée")

    def _send(self, ptype, payload):
        self.req += 1
        data = struct.pack("<ii", self.req, ptype) + payload.encode("utf-8") + b"\x00\x00"
        self.sock.sendall(struct.pack("<i", len(data)) + data)
        return self.req

    def _recv_exact(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("RCON fermé")
            buf += chunk
        return buf

    def _recv(self):
        (length,) = struct.unpack("<i", self._recv_exact(4))
        data = self._recv_exact(length)
        rid, ptype = struct.unpack("<ii", data[:8])
        return rid, ptype, data[8:-2].decode("utf-8", "replace")

    def cmd(self, command):
        rid = self._send(2, command)
        out = []
        r, _, body = self._recv()
        while r != rid:
            r, _, body = self._recv()
        out.append(body)
        # réponses longues : paquets supplémentaires de même id
        while len(body) >= 4000:
            self.sock.settimeout(0.5)
            try:
                r, _, body = self._recv()
                out.append(body)
            except (socket.timeout, TimeoutError):
                break
            finally:
                self.sock.settimeout(30)
        return "".join(out)

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


class Server:
    def __init__(self, sdir, world="Solstice", mods=(), extra_props=None, gamemode="adventure", vanilla=False):
        self.dir = sdir
        self.world = world
        self.mods = list(mods)
        self.proc = None
        self.rc = None
        self.extra_props = extra_props or {}
        self.gamemode = gamemode
        self.vanilla = vanilla

    # ---------- préparation ----------
    def prepare(self):
        os.makedirs(self.dir, exist_ok=True)
        for f in (("server.jar",) if self.vanilla else ("server.jar", "fabric-server-launch.jar")):
            dst = os.path.join(self.dir, f)
            if not os.path.exists(dst):
                shutil.copy(os.path.join(CACHE, "server", f), dst)
        # cache des bibliothèques Fabric partagé entre runs
        libs = os.path.join(CACHE, "fabric-libs")
        os.makedirs(libs, exist_ok=True)
        links = (("libraries", os.path.join(CACHE, "vanilla-libs")),) if self.vanilla else \
            (("libraries", libs), (".fabric", os.path.join(CACHE, "fabric-dot")))
        for name, target in links:
            os.makedirs(target, exist_ok=True)
            link = os.path.join(self.dir, name)
            rel = os.path.relpath(target, self.dir)   # lien relatif : le projet reste déplaçable
            if os.path.lexists(link) and os.readlink(link) != rel:
                os.remove(link)
            if not os.path.lexists(link):
                os.symlink(rel, link)
        mods_dir = os.path.join(self.dir, "mods")
        shutil.rmtree(mods_dir, ignore_errors=True)
        os.makedirs(mods_dir)
        for m in self.mods:
            shutil.copy(m, mods_dir)
        with open(os.path.join(self.dir, "fabric-server-launcher.properties"), "w") as f:
            f.write("serverJar=server.jar\n")
        with open(os.path.join(self.dir, "eula.txt"), "w") as f:
            f.write("# Serveur de test local du build SOLSTICE\neula=true\n")
        props = {
            "server-ip": "127.0.0.1", "server-port": GAME_PORT, "online-mode": "false",
            "enable-rcon": "true", "rcon.port": RCON_PORT, "rcon.password": RCON_PASS,
            "broadcast-rcon-to-ops": "false", "level-name": self.world, "level-type": "minecraft:flat",
            "generator-settings": VOID_GEN, "generate-structures": "false", "gamemode": self.gamemode,
            "difficulty": "normal", "spawn-protection": "0", "max-players": "6", "motd": "SOLSTICE test",
            "enable-query": "false", "view-distance": "6", "simulation-distance": "6",
            "function-permission-level": "2", "spawn-monsters": "true", "spawn-animals": "false",
            "sync-chunk-writes": "true", "enforce-secure-profile": "false", "white-list": "false",
            "log-ips": "false",
        }
        props.update(self.extra_props)
        with open(os.path.join(self.dir, "server.properties"), "w") as f:
            for k, v in props.items():
                v = str(v).replace("\\", "\\\\").replace(":", "\\:") if k == "generator-settings" else v
                f.write(f"{k}={v}\n")

    # ---------- cycle de vie ----------
    def start(self, timeout=600):
        self.prepare()
        log_dir = os.path.join(self.dir, "logs")
        if os.path.exists(os.path.join(log_dir, "latest.log")):
            os.remove(os.path.join(log_dir, "latest.log"))
        self.stdout = open(os.path.join(self.dir, "console.log"), "w")
        self.proc = subprocess.Popen(
            [java_bin(), "-Xms1G", "-Xmx3G", "-Djava.awt.headless=true",
             "-jar", "server.jar" if self.vanilla else "fabric-server-launch.jar", "--nogui"],
            cwd=self.dir, stdin=subprocess.PIPE, stdout=self.stdout, stderr=subprocess.STDOUT,
            start_new_session=True)
        atexit.register(self.kill)
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.proc.poll() is not None:
                raise RuntimeError("Le serveur s’est arrêté au démarrage, voir " + self.dir + "/console.log")
            if re.search(r"Done \([\d.,]+s\)!", self.console()):
                break
            time.sleep(1)
        else:
            raise TimeoutError("Serveur non prêt")
        for _ in range(30):
            try:
                self.rc = Rcon("127.0.0.1", RCON_PORT, RCON_PASS)
                break
            except OSError:
                time.sleep(1)
        print(f"  serveur prêt en {time.time() - t0:.0f}s")
        return self

    def console(self):
        try:
            with open(os.path.join(self.dir, "console.log"), encoding="utf-8", errors="replace") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def rcon(self, command):
        return self.rc.cmd(command)

    def stop(self):
        if not self.proc or self.proc.poll() is not None:
            return
        try:
            if self.rc:
                self.rc.cmd("save-all flush")
                self.rc._send(2, "stop")
        except (OSError, ConnectionError):
            pass
        try:
            self.proc.wait(timeout=90)
        except subprocess.TimeoutExpired:
            self.kill()
        if self.rc:
            self.rc.close()
        self.stdout.close()
        print("  serveur arrêté")

    def kill(self):
        if self.proc and self.proc.poll() is None:
            try:
                os.killpg(self.proc.pid, signal.SIGTERM)
                self.proc.wait(timeout=30)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                try:
                    os.killpg(self.proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
        self.kill()


def mod_paths(slugs):
    import json
    lock = json.load(open(os.path.join(CACHE, "mods.lock.json")))
    by = {m["slug"]: m for m in lock["mods"]}
    return [os.path.join(CACHE, "mods", by[s]["filename"]) for s in slugs]


if __name__ == "__main__":
    # smoke : démarre un serveur vide et l’arrête
    d = os.path.join(os.path.dirname(CACHE), "build", "server-smoke")
    with Server(d, world="smoke", vanilla=True) as s:
        print(s.rcon("list"))
        print(s.rcon("datapack list"))
