

module mux21
(
  a,
  b,
  s,
  y
);

  input a;input b;input s;
  output y;
  reg y;

  always @(a or b or s) if(s == 1'B0) begin
    y = a;
  end else y = b;


endmodule

