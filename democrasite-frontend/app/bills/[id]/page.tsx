import { Container, Center } from "@mantine/core";

import Bill from "@/components/Bill/Bill";
import fetchBills, { fetchBill } from "@/lib/fetch_bills";

export async function generateMetadata({
  params,
  searchParams,
}: {
  params: { id: number };
  searchParams: URLSearchParams;
}) {
  return { title: `${(await fetchBill(params.id)).name}` };
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
          <Bill bill={await fetchBill(params.id)} />
        </Container>
      </Center>
    </main>
  );
}

export async function generateStaticParams() {
  const bills = await fetchBills();

  return bills.map((bill: any) => ({
    id: bill.id.toString(),
  }));
}
