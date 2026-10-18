// Synthetic semantic/GC control; not yet a proven product-crash reproducer.
function assignAndReturn(target, value) {
  return (target.slot = value);
}
function exerciseSetLookup() {
  var target = { slot: null };
  var keep = [];
  for (var i = 0; i < 20000; ++i) {
    var expected = { token: i };
    var actual = assignAndReturn(target, expected);
    if (actual !== expected || target.slot !== expected)
      throw new Error("assignment identity changed at iteration " + i);
    keep.push(actual);
    if (keep.length > 128) keep.shift();
    if ((i % 256) === 0) {
      gc();
      for (var j = 0; j < keep.length; ++j) {
        if (keep[j].token !== i - keep.length + 1 + j)
          throw new Error("retained value changed after GC");
      }
    }
  }
  gc();
  return "QT_SETLOOKUP_PROBE_PASS";
}
exerciseSetLookup();
