
`timescale 1ns/10ps

module logic_gate (
    input wire a,
    input wire b,
    output wire c,
    output wire d,
    output wire e,
    output wire[1:0] f
);

assign c = a & b;
assign d = a | b;
assign e = a ^ b;
assign f = {a, b};


endmodule
