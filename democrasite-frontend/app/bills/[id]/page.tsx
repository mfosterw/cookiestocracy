import { Container, Center } from "@mantine/core";

import Bill from "@/components/Bill/Bill";
import { BillsApi } from "@/api/auto";

const api = new BillsApi();

export async function generateMetadata({
  params,
  searchParams,
}: {
  params: { id: number };
  searchParams: URLSearchParams;
}) {
  return {
    title: `${(await api.billsRetrieve({ id: params.id })).name}`,
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
          <Bill bill={await api.billsRetrieve({ id: params.id })} />
        </Container>
      </Center>
    </main>
  );
}

export async function generateStaticParams() {
  const bills = await api.billsList();

  return bills.map((bill: any) => ({
    id: bill.id.toString(),
  }));
}
