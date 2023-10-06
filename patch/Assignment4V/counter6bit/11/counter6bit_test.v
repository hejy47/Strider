

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

  always @(negedge CLR or posedge F_IN) begin
    if(CLR) Q <= 0; 
    else begin
      if(ENA) begin
        if(F_IN) begin
          if(Q[3:0] < 9) Q <= Q + 1; 
          else if(Q[7:4] < 9) begin
            Q[7:4] <= Q[7:4] + 1;
            Q[3:0] <= 0;
          end else if(Q[11:8] < 9) begin
            Q[11:8] <= Q[11:8] + 1;
            Q[7:0] <= 0;
          end else if(Q[15:12] < 9) begin
            Q[15:12] <= Q[15:12] + 1;
            Q[11:0] <= 0;
          end else if(Q[19:16] < 9) begin
            Q[19:16] <= Q[19:16] + 1;
            Q[15:0] <= 0;
          end else if(Q[23:20] < 9) begin
            Q[23:20] <= Q[23:20] + 1;
            Q[19:0] <= 0;
          end else Q <= 0;
        end 
      end 
    end
  end


endmodule

