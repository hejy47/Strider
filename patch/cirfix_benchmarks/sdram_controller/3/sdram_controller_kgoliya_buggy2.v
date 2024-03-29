

module sdram_controller
(
  wr_addr,
  wr_data,
  wr_enable,
  rd_addr,
  rd_data,
  rd_ready,
  rd_enable,
  busy,
  rst_n,
  clk,
  addr,
  bank_addr,
  data,
  clock_enable,
  cs_n,
  ras_n,
  cas_n,
  we_n,
  data_mask_low,
  data_mask_high
);

  parameter ROW_WIDTH = 13;
  parameter COL_WIDTH = 9;
  parameter BANK_WIDTH = 2;
  parameter SDRADDR_WIDTH = (ROW_WIDTH > COL_WIDTH)? ROW_WIDTH : COL_WIDTH;
  parameter HADDR_WIDTH = BANK_WIDTH + ROW_WIDTH + COL_WIDTH;
  parameter CLK_FREQUENCY = 133;
  parameter REFRESH_TIME = 32;
  parameter REFRESH_COUNT = 8192;
  localparam CYCLES_BETWEEN_REFRESH = CLK_FREQUENCY * 1_000 * REFRESH_TIME / REFRESH_COUNT;
  localparam IDLE = 5'b00000;
  localparam INIT_NOP1 = 5'b01000;localparam INIT_PRE1 = 5'b01001;localparam INIT_NOP1_1 = 5'b00101;localparam INIT_REF1 = 5'b01010;localparam INIT_NOP2 = 5'b01011;localparam INIT_REF2 = 5'b01100;localparam INIT_NOP3 = 5'b01101;localparam INIT_LOAD = 5'b01110;localparam INIT_NOP4 = 5'b01111;
  localparam REF_PRE = 5'b00001;localparam REF_NOP1 = 5'b00010;localparam REF_REF = 5'b00011;localparam REF_NOP2 = 5'b00100;
  localparam READ_ACT = 5'b10000;localparam READ_NOP1 = 5'b10001;localparam READ_CAS = 5'b10010;localparam READ_NOP2 = 5'b10011;localparam READ_READ = 5'b10100;
  localparam WRIT_ACT = 5'b11000;localparam WRIT_NOP1 = 5'b11001;localparam WRIT_CAS = 5'b11010;localparam WRIT_NOP2 = 5'b11011;
  localparam CMD_PALL = 8'b10010001;localparam CMD_REF = 8'b10001000;localparam CMD_NOP = 8'b10111000;localparam CMD_MRS = 8'b1000000x;localparam CMD_BACT = 8'b10011xxx;localparam CMD_READ = 8'b10101xx1;localparam CMD_WRIT = 8'b10100xx1;
  input [HADDR_WIDTH-1:0] wr_addr;
  input [15:0] wr_data;
  input wr_enable;
  input [HADDR_WIDTH-1:0] rd_addr;
  output [15:0] rd_data;
  input rd_enable;
  output rd_ready;
  output busy;
  input rst_n;
  input clk;
  output [12:0] addr;
  output [1:0] bank_addr;
  inout [15:0] data;
  output clock_enable;
  output cs_n;
  output ras_n;
  output cas_n;
  output we_n;
  output data_mask_low;
  output data_mask_high;
  reg [HADDR_WIDTH-1:0] haddr_r;
  reg [15:0] wr_data_r;
  reg [15:0] rd_data_r;
  reg busy;
  reg data_mask_low_r;
  reg data_mask_high_r;
  reg [SDRADDR_WIDTH-1:0] addr_r;
  reg [BANK_WIDTH-1:0] bank_addr_r;
  reg rd_ready_r;
  wire [15:0] data_output;
  wire data_mask_low;wire data_mask_high;
  assign data_mask_high = data_mask_high_r;
  assign data_mask_low = data_mask_low_r;
  assign rd_data = rd_data_r;
  reg [3:0] state_cnt;
  reg [9:0] refresh_cnt;
  reg [7:0] command;
  reg [4:0] state;
  reg [7:0] command_nxt;
  reg [3:0] state_cnt_nxt;
  reg [4:0] next;
  assign { clock_enable, cs_n, ras_n, cas_n, we_n } = command[7:3];
  assign bank_addr = (state[4])? bank_addr_r : command[2:1];
  assign addr = (state[4] | (state == INIT_LOAD))? addr_r : { { SDRADDR_WIDTH - 11{ 1'b0 } }, command[0], 10'd0 };
  assign data = (state == WRIT_CAS)? wr_data_r : 16'bz;
  assign rd_ready = rd_ready_r;

  always @(posedge clk) if(~rst_n) begin
    state <= INIT_NOP1;
    command <= CMD_NOP;
    state_cnt <= 4'hf;
    haddr_r <= { HADDR_WIDTH{ 1'b0 } };
    wr_data_r <= 16'b0;
    rd_data_r <= 16'b0;
    busy <= 1'b0;
  end else begin
    state <= next;
    command <= command_nxt;
    if(!state_cnt) state_cnt <= state_cnt_nxt; 
    else state_cnt <= state_cnt - 1'b1;
    if(wr_enable) wr_data_r <= wr_data; 
    if(state == READ_READ) begin
      rd_data_r <= data;
      rd_ready_r <= 1'b1;
    end else rd_ready_r <= 1'b0;
    busy <= state[4];
    if(rd_enable) haddr_r <= rd_addr; 
    else if(wr_enable) haddr_r <= wr_addr; 
  end


  always @(posedge clk) if(~rst_n) refresh_cnt <= 10'b0; 
  else if(state == REF_NOP2) refresh_cnt <= 10'b0; 
  else refresh_cnt <= refresh_cnt + 1'b1;


  always @(*) begin
    if(state[4]) { data_mask_low_r, data_mask_high_r } = 2'b00; 
    else { data_mask_low_r, data_mask_high_r } = 2'b11;
    bank_addr_r = 2'b00;
    addr_r = { SDRADDR_WIDTH{ 1'b0 } };
    if((state == READ_ACT) | (state == WRIT_ACT)) begin
      bank_addr_r = haddr_r[HADDR_WIDTH-1:HADDR_WIDTH-BANK_WIDTH];
      addr_r = haddr_r[HADDR_WIDTH-(BANK_WIDTH+1):HADDR_WIDTH-(BANK_WIDTH+ROW_WIDTH)];
    end else if((state == READ_CAS) | (state == WRIT_CAS)) begin
      bank_addr_r = haddr_r[HADDR_WIDTH-1:HADDR_WIDTH-BANK_WIDTH];
      addr_r = { { SDRADDR_WIDTH - 11{ 1'b0 } }, 1'b1, { 10 - COL_WIDTH{ 1'b0 } }, haddr_r[COL_WIDTH-1:0] };
    end else if(state == INIT_LOAD) begin
      addr_r = { { SDRADDR_WIDTH - 10{ 1'b0 } }, 10'b1000110000 };
    end 
  end


  always @(*) begin
    state_cnt_nxt = 4'd0;
    command_nxt = CMD_NOP;
    if(state == IDLE) if(refresh_cnt >= CYCLES_BETWEEN_REFRESH) begin
      next = REF_PRE;
      command_nxt = CMD_PALL;
    end else if(rd_enable) begin
      next = READ_ACT;
      command_nxt = CMD_BACT;
    end else if(wr_enable) begin
      next = WRIT_ACT;
      command_nxt = CMD_BACT;
    end else begin
      next = IDLE;
    end else if(!state_cnt) case(state)
      INIT_NOP1: begin
        next = INIT_PRE1;
        command_nxt = CMD_PALL;
      end
      INIT_PRE1: begin
        next = INIT_NOP1_1;
      end
      INIT_NOP1_1: begin
        next = INIT_REF1;
        command_nxt = CMD_REF;
      end
      INIT_REF1: begin
        next = INIT_NOP2;
        state_cnt_nxt = 4'd7;
      end
      INIT_NOP2: begin
        next = INIT_REF2;
        command_nxt = CMD_REF;
      end
      INIT_REF2: begin
        next = INIT_NOP3;
        state_cnt_nxt = 4'd7;
      end
      INIT_NOP3: begin
        next = INIT_LOAD;
        command_nxt = CMD_MRS;
      end
      INIT_LOAD: begin
        next = INIT_NOP4;
        state_cnt_nxt = 4'd1;
      end
      REF_PRE: begin
        next = REF_NOP1;
      end
      REF_NOP1: begin
        next = REF_REF;
        command_nxt = CMD_REF;
      end
      REF_REF: begin
        next = REF_NOP2;
        state_cnt_nxt = 4'd7;
      end
      WRIT_ACT: begin
        next = WRIT_NOP1;
        state_cnt_nxt = 4'd1;
      end
      WRIT_NOP1: begin
        next = WRIT_CAS;
        command_nxt = CMD_WRIT;
      end
      WRIT_CAS: begin
        next = WRIT_NOP2;
        state_cnt_nxt = 4'd1;
      end
      READ_ACT: begin
        next = READ_NOP1;
        state_cnt_nxt = 4'd1;
      end
      READ_NOP1: begin
        next = READ_CAS;
        command_nxt = CMD_READ;
      end
      READ_CAS: begin
        next = READ_NOP2;
        state_cnt_nxt = 4'd1;
      end
      READ_NOP2: begin
        next = READ_READ;
      end
      default: next = 5'b00000;
    endcase else begin
      next = state;
      command_nxt = command;
    end
  end


endmodule

