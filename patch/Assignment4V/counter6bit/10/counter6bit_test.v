

module counter6bit_test
(
  ENA,
  CLR,
  F_IN,
  Q
);

  input ENA;
  input CLR;
  input F_IN;
  output [23:0] Q;
  reg [23:0] Q;
  reg F_OUT;

  always @(posedge CLR or posedge F_IN or posedge ENA) begin
    if(CLR) if(F_IN) Q <= 'b000000000000000000000000; 
    else Q <= Q; else if(!ENA) Q <= Q; 
    else if(Q[3:0] == 4'd9) begin
      Q[7:4] <= Q[7:4] + 1;
      Q[3:0] = 0;
    end else Q <= Q + 1;
  end


endmodule

