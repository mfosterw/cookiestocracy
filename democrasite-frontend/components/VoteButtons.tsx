"use client";

import { Reducer, useReducer, useState } from "react";
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

type VoteAction =
  | { type: "vote"; vote: "yes" | "no" }
  | ({ type: "update" } & VoteCounts)
  | { type: "openTooltip"; vote: "yes" | "no"; timeout?: NodeJS.Timeout };

type VoteState = {
  vote: "yes" | "no" | null;
  yesVotes: number;
  noVotes: number;
  yesTooltipOpenTimeout?: NodeJS.Timeout;
  noTooltipOpenTimeout?: NodeJS.Timeout;
};

const voteReducer: Reducer<VoteState, VoteAction> = (state, action) => {
  switch (action.type) {
    case "vote": {
      const yesVotesDiff =
        state.vote === "yes" ? -1 : action.vote === "yes" ? 1 : 0;
      const noVotesDiff =
        state.vote === "no" ? -1 : action.vote === "no" ? 1 : 0;
      const newVote = state.vote === action.vote ? null : action.vote;
      return {
        ...state,
        yesVotes: state.yesVotes + yesVotesDiff,
        noVotes: state.noVotes + noVotesDiff,
        vote: newVote,
      };
    }
    case "update":
      return { ...state, yesVotes: action.yesVotes, noVotes: action.noVotes };

    case "openTooltip":
      // set id for state.yesTooltipOpenTimeout or state.no...
      if (state[`${action.vote}TooltipOpenTimeout`] !== undefined) {
        clearTimeout(state[`${action.vote}TooltipOpenTimeout`]);
      }
      return {
        ...state,
        [`${action.vote}TooltipOpenTimeout`]: action.timeout,
      };
    default:
      throw Error("Invalid action type");
  }
};

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
  const userVote =
    userSupports === true ? "yes" : userSupports === false ? "no" : null;
  const [state, dispatch] = useReducer(voteReducer, {
    vote: userVote,
    yesVotes,
    noVotes,
  });

  const { status: authStatus } = useSession();
  // const session = await auth();
  // See BillList.tsx to understand the difficulty of accessing the session
  const [isVoting, setIsVoting] = useState(false);

  const handleVote = async (newVote: "yes" | "no") => {
    if (authStatus !== "authenticated") {
      dispatch({
        type: "openTooltip",
        vote: newVote,
        timeout: setTimeout(() => {
          dispatch({ type: "openTooltip", vote: newVote, timeout: undefined });
        }, 3000),
      });
    }

    // Disable voting while a vote is being processed
    setIsVoting(true);

    dispatch({ type: "vote", vote: newVote });

    try {
      const voteCounts = await billsVote({
        id,
        vote: { support: newVote === "yes" },
      });
      dispatch({ type: "update", ...voteCounts });
    } catch (error) {
      console.error("Failed to cast vote", error);
    } finally {
      // Re-enable voting after the vote has been processed
      setIsVoting(false);
    }
  };

  function VoteButton({ voteType }: { voteType: "yes" | "no" }) {
    const loading = !disabled && (isVoting || authStatus === "loading");
    return (
      <Tooltip
        label="You must be logged in to vote"
        opened={state[`${voteType}TooltipOpenTimeout`] !== undefined}
        color="blue"
        withArrow
      >
        <ActionIcon
          color={voteType === "yes" ? "green" : "red"}
          variant={state.vote === voteType ? "filled" : "outline"}
          disabled={disabled}
          loading={loading}
          onClick={() => {
            void handleVote(voteType);
          }}
        >
          <ThumbIcon
            type={voteType === "yes" ? "up" : "down"}
            selected={state.vote === voteType}
          />
        </ActionIcon>
      </Tooltip>
    );
  }

  return (
    <Group justify="space-between">
      <Group c="green">
        <VoteButton voteType="yes" />
        <Text>{state.yesVotes}</Text>
      </Group>
      <Group c="red">
        <Text>{state.noVotes}</Text>
        <VoteButton voteType="no" />
      </Group>
    </Group>
  );
}
