

module JG3
(
  ABC,
  X,
  Y
);

  input [2:0] ABC;
  output X;
  output Y;
  reg X;
  reg Y;

  always @(ABC) case(ABC)
    3'b000: begin
      X = 1'b0;
      Y = 1'b1;
    end
    3'b001: begin
      X = 1'b0;
      Y = 1'b0;
    end
    3'b010: begin
      X = 1'b0;
      Y = 1'b0;
    end
    3'b011: begin
      X = 1'b0;
      Y = 1'b0;
    end
    3'b100: begin
      X = 1'b0;
      Y = 1'b0;
    end
    3'b000: begin
      X = 1'b0;
      Y = 1'b1;
    end
    3'b000: begin
      X = 1'b0;
      Y = 1'b0;
    end
    3'b000: begin
      X = 1'b0;
      Y = 1'b0;
    end
    default: begin
      X = 1'b1;
      Y = 1'b0;
    end
  endcase


endmodule

