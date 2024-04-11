import { Title, Text, Anchor, Divider, Stack, Container } from "@mantine/core";
import { type Bill } from "@/lib/models";
import { VoteButtons } from "@/components";

export function Bill({ bill }: { bill: Bill }) {
  return (
    <Stack>
      <Container ta="center">
        <Anchor href={`/bills/${bill.id.toString()}`}>
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
      <VoteButtons
        id={bill.id}
        disabled={bill.status !== "Open"}
        userSupports={bill.userSupports}
        yesVotes={bill.yesVotes}
        noVotes={bill.noVotes}
      ></VoteButtons>
    </Stack>
  );
}
