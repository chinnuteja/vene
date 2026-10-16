// One place for platform differences. Windows paths are unchanged from Phases 1-8.
import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';

export const isWindows = process.platform === 'win32';

export function venvPython(root) {
  return path.join(root, isWindows ? '.venv/Scripts/python.exe' : '.venv/bin/python');
}

export function livekitBinary(root) {
  const owned = path.join(root, '.local/tools/livekit', isWindows ? 'livekit-server.exe' : 'livekit-server');
  if (existsSync(owned)) return owned;
  if (process.platform === 'darwin') {
    // No pinned macOS archive exists for this release; use an explicitly installed server.
    const found = spawnSync('which', ['livekit-server'], { encoding: 'utf8' });
    if (found.status === 0 && found.stdout.trim()) return found.stdout.trim();
  }
  return owned;
}
