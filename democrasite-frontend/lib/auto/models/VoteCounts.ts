/* tslint:disable */
/* eslint-disable */
/**
 * Democrasite API
 * Documentation of API endpoints of Democrasite
 *
 * The version of the OpenAPI document: 1.0.0
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import { exists, mapValues } from '../runtime';
/**
 *
 * @export
 * @interface VoteCounts
 */
export interface VoteCounts {
    /**
     *
     * @type {number}
     * @memberof VoteCounts
     */
    yesVotes: number;
    /**
     *
     * @type {number}
     * @memberof VoteCounts
     */
    noVotes: number;
}

/**
 * Check if a given object implements the VoteCounts interface.
 */
export function instanceOfVoteCounts(value: object): boolean {
    let isInstance = true;
    isInstance = isInstance && "yesVotes" in value;
    isInstance = isInstance && "noVotes" in value;

    return isInstance;
}

export function VoteCountsFromJSON(json: any): VoteCounts {
    return VoteCountsFromJSONTyped(json, false);
}

export function VoteCountsFromJSONTyped(json: any, ignoreDiscriminator: boolean): VoteCounts {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {

        'yesVotes': json['yes_votes'],
        'noVotes': json['no_votes'],
    };
}

export function VoteCountsToJSON(value?: VoteCounts | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {

        'yes_votes': value.yesVotes,
        'no_votes': value.noVotes,
    };
}
