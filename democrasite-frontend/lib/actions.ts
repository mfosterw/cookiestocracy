"use server";

import { billsApi } from "./api";
import { BillsVoteCreateRequest } from "./auto";

// Server actions to call on client side
export const billsVote = async (params: BillsVoteCreateRequest) =>
  await billsApi.billsVoteCreate(params);
