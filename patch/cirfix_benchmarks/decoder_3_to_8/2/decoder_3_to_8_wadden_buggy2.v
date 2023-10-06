

module decoder_3to8
(
  Y7,
  Y6,
  Y5,
  Y4,
  Y3,
  Y2,
  Y1,
  Y0,
  A,
  B,
  C,
  en
);

  output Y7;
  output Y6;
  output Y5;
  output Y4;
  output Y3;
  output Y2;
  output Y1;
  output Y0;
  input A;
  input B;
  input C;
  input en;
  assign { Y7, Y6, Y5, Y4, Y3, Y2, Y1, Y0 } = ({ en, A, B, C } == 4'b1000)? 'b11111110 : 
                                              ({ en, A, B, C } == 4'b1001)? 8'b1111101 : 
                                              ({ en, A, B, C } == 4'b1010)? 'b11111011 : 
                                              ({ en, A, B, C } == 4'b1011)? 8'b1110111 : 
                                              ({ en, A, B, C } == 4'b1100)? 'b11101111 : 
                                              ({ en, A, B, C } == 4'b1101)? 8'b1011111 : 
                                              ({ en, A, B, C } == 4'b1110)? 'b10111111 : 
                                              ({ en, A, B, C } == 4'b1111)? 8'b1111111 : 'b11111111;

endmodule

