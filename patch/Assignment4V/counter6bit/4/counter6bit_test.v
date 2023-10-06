

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
  reg [19:0] temp_bcd = 0;
  reg F_OUT;

  always @(posedge F_IN) begin
    if(CLR == 1) Q <= 0; 
    else begin
      if(ENA == 1) begin
        if(Q[3:0] == 4'b1001) begin
          temp_bcd <= temp_bcd + 1;
          if(temp_bcd) if(Q == 'b000000000000000000101001) Q <= 'b000000000000000000110000; 
          else if(Q == 'b000000000000000000111001) Q <= 'b000000000000000001000000; 
          else if(Q == 'b000000000000000001001001) Q <= 'b000000000000000001010000; 
          else if(Q == 'b000000000000000001011001) Q <= 'b000000000000000001100000; 
          else if(Q == 'b000000000000000001101001) Q <= 'b000000000000000001110000; 
          else if(Q == 'b000000000000000001111001) Q <= 'b000000000000000010000000; 
          else Q <= 'b000000000000000000100000; else Q <= 'b000000000000000000010000;
        end else if(Q[7:0] == 8'b10000000) Q <= 0; 
        else Q = Q + 1;
      end 
    end
  end


endmodule

