import {
  Title,
  Text,
  Anchor,
  Divider,
  Group,
  Stack,
  Center,
  Container,
} from "@mantine/core";

export default function Bill({ bill }: any) {
  return (
    <Stack>
      <Container ta="center">
        <Anchor href={`/bills/${bill.id}`}>
          <Title order={3}>
            Bill {bill.id}: {bill.name} (PR&nbsp;#{bill.pull_request.number})
          </Title>
        </Anchor>
        {bill.constitutional && <Text c="cyan">Constitutional Amendment</Text>}
        {bill.status != "Open" && (
          <Text c={bill.status == "Approved" ? "green" : "red"}>
            {bill.status}
          </Text>
        )}
      </Container>
      <Divider />
      <Text lineClamp={3}>{bill.description}</Text>
      <Anchor href={bill.pull_request.diff_url} ta="right" right="0">
        <Text span c="green">
          +{bill.pull_request.additions}
        </Text>
        <Text span c="red" ml="sm">
          -{bill.pull_request.deletions}
        </Text>
      </Anchor>
      <Group justify="space-between">
        <Group>
          <Text c="green">Yes: {bill.yes_votes.length}</Text>
        </Group>
        <Group>
          <Text c="red">No: {bill.no_votes.length}</Text>
        </Group>
      </Group>
    </Stack>
  );
}
