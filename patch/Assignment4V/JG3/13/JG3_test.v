

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
    3'B000: begin
      X <= 1'B0;
      Y <= 1'B1;
    end
    3'B001: begin
      X <= 1'B0;
      Y <= 1'B0;
    end
    3'B010: begin
      X <= 1'B0;
      Y <= 1'B0;
    end
    3'B100: begin
      X <= 1'B0;
      Y <= 1'B0;
    end
    3'B110: begin
      X <= 'b1;
      Y <= 1'B0;
    end
    3'B101: begin
      X <= 1'B1;
      Y <= 1'B0;
    end
    3'B011: begin
      X <= 'b0;
      Y <= 1'B0;
    end
    3'B111: begin
      X <= 1'B1;
      Y <= 1'B0;
    end
    default: begin
    end
  endcase


endmodule

