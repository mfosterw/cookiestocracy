import { Container, Center } from "@mantine/core";

import { Bill } from "@/components";
import api from "@/lib/api";

export async function generateMetadata({ params }: { params: { id: number } }) {
  return {
    title: `${(await api.billsApi.billsRetrieve({ id: params.id })).name}`,
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
          <Bill bill={await api.billsApi.billsRetrieve({ id: params.id })} />
        </Container>
      </Center>
    </main>
  );
}

export async function generateStaticParams() {
  const bills = await api.billsApi.billsList();

  return bills.map((bill: any) => ({
    id: bill.id.toString(),
  }));
}
