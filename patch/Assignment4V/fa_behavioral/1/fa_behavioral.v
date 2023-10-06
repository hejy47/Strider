

module fa_behavioral
(
  a,
  b,
  ci,
  s,
  co
);

  input a;
  input b;
  input ci;
  output s;
  output co;
  assign s = (b)? (ci)? a : ci : a | b | ci;
  assign co = a & b | a & ci | b & ci;

endmodule

