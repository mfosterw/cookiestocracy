import { Container, Center } from "@mantine/core";

import { Bill } from "@/components";
import { billsApi } from "@/lib/api";
import type { Bill as BillType } from "@/lib/models";

export async function generateMetadata({ params }: { params: { id: number } }) {
  return {
    title: (await billsApi.billsRetrieve({ id: params.id })).name,
  };
}

export default async function BillDetail({
  params,
}: {
  params: { id: number };
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-32">
      <Center h="100%">
        <Container size="xs">
          <Bill bill={await billsApi.billsRetrieve({ id: params.id })} />
        </Container>
      </Center>
    </main>
  );
}

export async function generateStaticParams() {
  const bills = await billsApi.billsList();

  return bills.map((bill: BillType) => ({
    id: bill.id.toString(),
  }));
}
