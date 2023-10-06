

module decoder3e_test
(
  a,
  ena,
  y
);

  input [2:0] a;
  input ena;
  output [7:0] y;
  reg [7:0] y;

  always @(a or ena) begin
    if(~ena) y = 8'd0; 
    else case(a)
      3'b000: y <= 8'd1;
      3'b001: y <= 8'd2;
      3'b010: y <= 'b00000100;
      3'b011: y <= 8'd8;
      3'b100: y <= 8'd16;
      3'b101: y <= 8'd32;
      3'b110: y <= 8'd64;
      3'b111: y <= 8'd128;
    endcase
  end


endmodule

