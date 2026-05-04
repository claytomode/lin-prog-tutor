export const docExamples: Record<string, string> = {
  bakery_lp: `maximize 30 x + 20 y
subject to
2 x + y <= 100
x + 2 y <= 80
x >= 0
y >= 0`,
  lp_corner_demo: `maximize 3 x + 2 y
subject to
x + y <= 4
x >= 0
y >= 0`,
  primal_dual_primal: `maximize 3 x1 + 2 x2
subject to
x1 + x2 <= 4
x1 <= 2
x1 >= 0
x2 >= 0`,
  warehouse_milp: `minimize 18 x11 + 22 x12 + 20 x21 + 16 x22 + 70 y1 + 60 y2
subject to
x11 + x21 >= 8
x12 + x22 >= 6
x11 + x12 <= 12 y1
x21 + x22 <= 10 y2
x11 >= 0
x12 >= 0
x21 >= 0
x22 >= 0
variables:
y1 binary
y2 binary`,
  campaign_binary: `maximize 8 y_a + 7 y_b + 6 y_c
subject to
5 y_a + 4 y_b + 3 y_c <= 7
variables:
y_a binary
y_b binary
y_c binary`,
};

