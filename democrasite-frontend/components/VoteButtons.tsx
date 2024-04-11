"use client";

import { useState } from "react";
import { ActionIcon, Group, Text, Tooltip } from "@mantine/core";
import { useSession } from "next-auth/react";
import { billsVote } from "@/lib/actions";
import { VoteCounts } from "@/lib/models";

interface ThumbProps {
  type: "up" | "down";
  color?: string;
  size?: number;
  selected?: boolean;
  onClick?: () => void;
}

const thumbIcons = {
  up: (
    <path d="M7 11v8a1 1 0 0 1 -1 1h-2a1 1 0 0 1 -1 -1v-7a1 1 0 0 1 1 -1h3a4 4 0 0 0 4 -4v-1a2 2 0 0 1 4 0v5h3a2 2 0 0 1 2 2l-1 5a2 3 0 0 1 -2 2h-7a3 3 0 0 1 -3 -3" />
  ),
  down: (
    <path d="M7 13v-8a1 1 0 0 0 -1 -1h-2a1 1 0 0 0 -1 1v7a1 1 0 0 0 1 1h3a4 4 0 0 1 4 4v1a2 2 0 0 0 4 0v-5h3a2 2 0 0 0 2 -2l-1 -5a2 3 0 0 0 -2 -2h-7a3 3 0 0 0 -3 3" />
  ),
};

const ThumbIcon: React.FC<ThumbProps> = ({
  type,
  color = "currentColor",
  size = 24,
  selected = false,
  onClick,
}) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className={`icon icon-tabler icon-tabler-thumb-${type}`}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    strokeWidth="1.5"
    stroke={selected ? "white" : color}
    fill="none"
    strokeLinecap="round"
    strokeLinejoin="round"
    onClick={onClick}
  >
    <path stroke="none" d="M0 0h24v24H0z" fill="none" />
    {thumbIcons[type]}
  </svg>
);

export function VoteButtons({
  id,
  disabled,
  userSupports,
  yesVotes,
  noVotes,
}: {
  id: number;
  disabled: boolean;
  userSupports: boolean | null;
} & VoteCounts) {
  const [vote, setVote] = useState<"yes" | "no" | null>(
    userSupports ? "yes" : userSupports === false ? "no" : null,
  );
  const [yesVotesCount, setYesVotes] = useState<number>(yesVotes);
  const [noVotesCount, setNoVotes] = useState<number>(noVotes);
  const { status } = useSession();
  // const session = await auth();
  // See BillList.tsx to understand the difficulty of accessing the session
  const [isVoting, setIsVoting] = useState(false);

  const handleVote = async (newVote: "yes" | "no") => {
    if (status !== "authenticated") {
      alert("You must be signed in to vote");
      return;
    }

    // Disable voting while a vote is being processed
    setIsVoting(true);

    const yesVotesDiff = vote === "yes" ? -1 : newVote === "yes" ? 1 : 0;
    setYesVotes((current) => current + yesVotesDiff);
    const noVotesDiff = vote === "no" ? -1 : newVote === "no" ? 1 : 0;
    setNoVotes((current) => current + noVotesDiff);

    setVote((currentVote) => (currentVote === newVote ? null : newVote));

    try {
      const { yesVotes, noVotes } = await billsVote({
        id,
        vote: { support: newVote === "yes" },
      });
      setYesVotes(yesVotes);
      setNoVotes(noVotes);
    } catch (error) {
      console.error("Failed to cast vote", error);
    } finally {
      // Re-enable voting after the vote has been processed
      setIsVoting(false);
    }
  };

  function VoteButton({ voteType }: { voteType: "yes" | "no" }) {
    const [tooltipOpen, setTooltipOpen] = useState(false);
    return (
      <Tooltip
        label="You must be logged in to vote"
        opened={tooltipOpen}
        color="blue"
        withArrow
      >
        <ActionIcon
          color={voteType === "yes" ? "green" : "red"}
          variant={vote === voteType ? "filled" : "outline"}
          loading={isVoting || status === "loading"}
          disabled={disabled}
          onClick={() => {
            if (status !== "authenticated") {
              setTooltipOpen((current) => {
                if (!current) {
                  setTimeout(() => {
                    setTooltipOpen(false);
                  }, 3000);
                }
                return !current;
              });
              return;
            }
            void handleVote(voteType);
          }}
        >
          <ThumbIcon
            type={voteType === "yes" ? "up" : "down"}
            selected={vote === voteType}
          />
        </ActionIcon>
      </Tooltip>
    );
  }

  return (
    <Group justify="space-between">
      <Group c="green">
        <VoteButton voteType="yes" />
        <Text>{yesVotesCount}</Text>
      </Group>
      <Group c="red">
        <Text>{noVotesCount}</Text>
        <VoteButton voteType="no" />
      </Group>
    </Group>
  );
}
