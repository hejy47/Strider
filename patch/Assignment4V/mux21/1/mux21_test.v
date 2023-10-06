

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

  always @(a or b or s) if(s == 'b0) y = a; 
  else y = b;


endmodule

