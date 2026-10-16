#!/usr/bin/env bash
# Installs the pinned official LiveKit server for this platform and generates local credentials.
source "$(dirname "$0")/common.sh"
require_runtime
case "$(uname -s)-$(uname -m)" in
  Linux-x86_64) key=linux-x64 ;;
  Linux-aarch64|Linux-arm64) key=linux-arm64 ;;
  Darwin-*) key=darwin ;;
  *) echo "Unsupported platform for the pinned LiveKit server: $(uname -s)-$(uname -m)" >&2; exit 1 ;;
esac
TOOL="$PROJECT_ROOT/.local/tools/livekit"
mkdir -p "$TOOL" .local/downloads
if [ "$key" = darwin ]; then
  command -v livekit-server >/dev/null 2>&1 || { echo 'No pinned macOS LiveKit archive exists for this release. Install livekit-server (for example: brew install livekit) and rerun.' >&2; exit 1; }
  livekit-server --version
  echo 'Using livekit-server from PATH (not checksum-pinned).'
else
  read -r source sha < <(node -e "const p=JSON.parse(require('fs').readFileSync('infra/livekit-binary.json','utf8')).platforms[process.argv[1]];console.log(p.source+' '+p.sha256)" "$key")
  archive=".local/downloads/$(basename "$source")"
  [ -f "$archive" ] || curl -sSLf -o "$archive" "$source"
  actual="$(sha256sum "$archive" 2>/dev/null | cut -d' ' -f1 || shasum -a 256 "$archive" | cut -d' ' -f1)"
  [ "$actual" = "$sha" ] || { rm -f "$archive"; echo 'LiveKit archive checksum does not match the pinned official release.' >&2; exit 1; }
  [ -x "$TOOL/livekit-server" ] || tar -xzf "$archive" -C "$TOOL" livekit-server
  "$TOOL/livekit-server" --version
fi
node -e "
  const fs=require('fs'),crypto=require('crypto');const file=process.argv[1];
  const r=JSON.parse(fs.readFileSync(file,'utf8').replace(/^﻿/,''));
  r.livekit_key??='vene_'+crypto.randomBytes(16).toString('hex');
  r.livekit_secret??=crypto.randomBytes(32).toString('hex');
  r.livekit_port??=7880;r.livekit_tcp_port??=7881;r.livekit_udp_port??=7882;r.livekit_turn_port??=3478;
  fs.writeFileSync(file,JSON.stringify(r,null,2)+'\n');
" "$RUNTIME"
echo 'Pinned local LiveKit installed. Credentials saved only in ignored runtime state.'
