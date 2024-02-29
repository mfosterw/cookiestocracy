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
import type { PullRequest } from './PullRequest';
import {
    PullRequestFromJSON,
    PullRequestFromJSONTyped,
    PullRequestToJSON,
} from './PullRequest';
import type { User } from './User';
import {
    UserFromJSON,
    UserFromJSONTyped,
    UserToJSON,
} from './User';

/**
 *
 * @export
 * @interface Bill
 */
export interface Bill {
    /**
     *
     * @type {number}
     * @memberof Bill
     */
    readonly id: number;
    /**
     *
     * @type {User}
     * @memberof Bill
     */
    author: User;
    /**
     *
     * @type {PullRequest}
     * @memberof Bill
     */
    readonly pullRequest: PullRequest;
    /**
     *
     * @type {string}
     * @memberof Bill
     */
    status: string;
    /**
     *
     * @type {Array<string>}
     * @memberof Bill
     */
    readonly yesVotes: Array<string>;
    /**
     *
     * @type {Array<string>}
     * @memberof Bill
     */
    readonly noVotes: Array<string>;
    /**
     *
     * @type {Date}
     * @memberof Bill
     */
    readonly created: Date;
    /**
     *
     * @type {Date}
     * @memberof Bill
     */
    statusChanged?: Date;
    /**
     *
     * @type {string}
     * @memberof Bill
     */
    name: string;
    /**
     *
     * @type {string}
     * @memberof Bill
     */
    description?: string;
    /**
     * True if this bill is an amendment to the constitution
     * @type {boolean}
     * @memberof Bill
     */
    readonly constitutional: boolean;
}

/**
 * Check if a given object implements the Bill interface.
 */
export function instanceOfBill(value: object): boolean {
    let isInstance = true;
    isInstance = isInstance && "id" in value;
    isInstance = isInstance && "author" in value;
    isInstance = isInstance && "pullRequest" in value;
    isInstance = isInstance && "status" in value;
    isInstance = isInstance && "yesVotes" in value;
    isInstance = isInstance && "noVotes" in value;
    isInstance = isInstance && "created" in value;
    isInstance = isInstance && "name" in value;
    isInstance = isInstance && "constitutional" in value;

    return isInstance;
}

export function BillFromJSON(json: any): Bill {
    return BillFromJSONTyped(json, false);
}

export function BillFromJSONTyped(json: any, ignoreDiscriminator: boolean): Bill {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {

        'id': json['id'],
        'author': UserFromJSON(json['author']),
        'pullRequest': PullRequestFromJSON(json['pull_request']),
        'status': json['status'],
        'yesVotes': json['yes_votes'],
        'noVotes': json['no_votes'],
        'created': (new Date(json['created'])),
        'statusChanged': !exists(json, 'status_changed') ? undefined : (new Date(json['status_changed'])),
        'name': json['name'],
        'description': !exists(json, 'description') ? undefined : json['description'],
        'constitutional': json['constitutional'],
    };
}

export function BillToJSON(value?: Bill | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {

        'author': UserToJSON(value.author),
        'status': value.status,
        'status_changed': value.statusChanged === undefined ? undefined : (value.statusChanged.toISOString()),
        'name': value.name,
        'description': value.description,
    };
}
