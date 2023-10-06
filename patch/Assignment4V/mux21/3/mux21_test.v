

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

  always @(a or b or s) begin
    case(s)
      1'b0: begin
        y = a;
      end
      'b1: begin
        y = b;
      end
      default: begin
        y = 0;
      end
    endcase
  end


endmodule

