

module latch24_test
(
  d,
  clk,
  q
);

  input [23:0] d;
  input clk;
  output [23:0] q;
  reg [23:0] q;

  always @(posedge clk) q = d;


endmodule

