"use client";

// TODO: This has to be a client component because it uses SessionProvider
// This could be avoided by using getServerSession in Bill.tsx but that would
// require making Bill async, which would also force this to be a client component
// due to Mantine. It may be worth it to ugrapde to Auth.js v5 before it leaves beta
// to make sessions more convenient.
import { Card, Grid, GridCol } from "@mantine/core";
import { Bill } from "@/components";
import type { Bill as BillType } from "@/lib/models";
import { SessionProvider } from "next-auth/react";

export function BillList({ bill_list }: { bill_list: BillType[] }) {
  const cards = bill_list.map((bill: BillType) => (
    <GridCol key={bill.id} span={{ base: 12, sm: 6, md: 4, lg: 3 }}>
      <Card shadow="md" padding="lg" radius="sm" withBorder>
        <Bill bill={bill} />
      </Card>
    </GridCol>
  ));

  return (
    <SessionProvider>
      <Grid gutter={{ base: 5, xs: "md", xl: "xl" }}>{cards}</Grid>
    </SessionProvider>
  );
}
