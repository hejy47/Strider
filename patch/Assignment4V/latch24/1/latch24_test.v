

module latch24_test
(
  d,
  clk,
  q
);

  input [23:0] d;wire [23:0] d;
  input clk;wire clk;
  output [23:0] q;wire [23:0] q;
  reg [23:0] q_reg;

  always @(posedge clk) begin
    q_reg <= d;
  end

  assign q = q_reg;

endmodule

