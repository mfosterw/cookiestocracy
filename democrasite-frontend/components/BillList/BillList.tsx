import { Card, Grid, GridCol } from "@mantine/core";
import Bill from "../../components/Bill/Bill";

const bills = [
  {
    name: "test",
    description: "This is a test",
    time_created: "2024-02-19T00:05:35.164799-06:00",
    author: "http://127.0.0.1:8000/api/users/matthew/",
    pull_request: "http://127.0.0.1:8000/api/pull-requests/-1/",
    yes_votes: [],
    no_votes: ["http://127.0.0.1:8000/api/users/mfosterw/"],
    url: "http://127.0.0.1:8000/api/bills/1/",
  },
  {
    name: "hi",
    description:
      "This bill has an extremely long-winded description. In fact, the description is so long that it will have to be cut off when being displayed. That makes it a pretty long description in my opinion.",
    time_created: "2024-02-19T00:05:35.164799-06:00",
    author: "http://127.0.0.1:8000/api/users/matthew/",
    pull_request: "http://127.0.0.1:8000/api/pull-requests/-2/",
    yes_votes: ["http://127.0.0.1:8000/api/users/mfosterw/"],
    no_votes: [],
    url: "http://127.0.0.1:8000/api/bills/18/",
  },
];

export default function BillList(props: any) {
  const cards = props.bill_list.map((bill: any) => (
    <GridCol key={bill.id} span={{ base: 12, sm: 6, md: 4, lg: 3 }}>
      <Card shadow="md" padding="lg" radius="sm" withBorder>
        <Bill bill={bill} />
      </Card>
    </GridCol>
  ));

  return <Grid gutter={{ base: 5, xs: "md", xl: "xl" }}>{cards}</Grid>;
}
