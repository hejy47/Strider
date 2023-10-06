

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

  always @(F_IN or ENA or CLR) begin
    if(CLR == 1) if(F_IN) Q <= 'b000000000000000000000000; 
    else Q <= Q; else if(ENA == 0) Q <= Q; 
    else if(F_IN == 1) begin
      if(Q[3:0] == 4'b1001) begin
        Q[3:0] <= 4'b0000;
        if(Q[7:4] == 4'b1001) begin
          Q[7:4] <= 4'b0000;
          if(Q[11:8] == 4'b1001) begin
            Q[11:8] <= 4'b0000;
            if(Q[15:11] == 4'b1001) begin
              Q[14:11] <= 4'b0000;
              if(Q[19:16] == 4'b1001) begin
                Q[19:16] <= 4'b0000;
                if(Q[23:20] == 4'b1001) Q[23:20] <= 4'b0000; 
                else Q[23:20] <= Q[24:20] + 1;
              end else Q[19:16] <= Q[19:16] + 1;
            end else Q[15:11] <= Q[15:11] + 1;
          end else Q[11:8] <= Q[11:8] + 1;
        end else Q[7:4] <= Q[7:4] + 1;
      end else Q[3:0] <= Q[3:0] + 1;
    end else Q[23:0] <= Q[23:0];
  end


endmodule

