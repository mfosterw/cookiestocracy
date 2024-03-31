import { Bill } from "@/lib";
import {
  Title,
  Text,
  Anchor,
  Divider,
  Group,
  Stack,
  Container,
} from "@mantine/core";

export function Bill({ bill }: { bill: Bill }) {
  return (
    <Stack>
      <Container ta="center">
        <Anchor href={`/bills/${bill.id}`}>
          {bill.userSupports !== null && "⭐️"}
          <Title order={3}>
            Bill {bill.id}: {bill.name} (PR&nbsp;#{bill.pullRequest.number})
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
      <Anchor href={bill.pullRequest.diffUrl} ta="right" right="0">
        <Text span c="green">
          +{bill.pullRequest.additions}
        </Text>
        <Text span c="red" ml="sm">
          -{bill.pullRequest.deletions}
        </Text>
      </Anchor>
      <Group justify="space-between">
        <Group>
          <Text c="green">Yes: {bill.yesVotes.length}</Text>
        </Group>
        <Group>
          <Text c="red">No: {bill.noVotes.length}</Text>
        </Group>
      </Group>
    </Stack>
  );
}
