/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : L-2016.03-SP1
// Date      : Thu Apr  4 20:17:18 2024
/////////////////////////////////////////////////////////////


module logic_gate ( a, b, c, d, e, f );
  output [1:0] f;
  input a, b;
  output c, d, e;
  wire   n2;
  assign f[1] = a;
  assign f[0] = b;

  INVHDMX U5 ( .A(n2), .Z(d) );
  AND2HDMX U6 ( .A(f[1]), .B(f[0]), .Z(c) );
  NOR2HDUX U7 ( .A(f[1]), .B(f[0]), .Z(n2) );
  NOR2HDUX U8 ( .A(c), .B(n2), .Z(e) );
endmodule
