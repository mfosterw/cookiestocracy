import { Card, Grid, GridCol } from "@mantine/core";
import { Bill } from "@/components";
import type { Bill as BillType } from "@/lib/models";

export function BillList({ bill_list }: { bill_list: BillType[] }) {
  const cards = bill_list.map((bill: BillType) => (
    <GridCol key={bill.id} span={{ base: 12, sm: 6, md: 4, lg: 3 }}>
      <Card shadow="md" padding="lg" radius="sm" withBorder>
        <Bill bill={bill} />
      </Card>
    </GridCol>
  ));

  return <Grid gutter={{ base: 5, xs: "md", xl: "xl" }}>{cards}</Grid>;
}
