// A supervisor owns the destination's lifetime, including across restarts.
// Child stdout/stderr ending must not end the shared log destination.
export function pipeOwnedOutput(child, destination) {
  child.stdout.pipe(destination, {end:false});
  child.stderr.pipe(destination, {end:false});
}
