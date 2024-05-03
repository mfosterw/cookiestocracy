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
import type { UserRequest } from './UserRequest';
import {
    UserRequestFromJSON,
    UserRequestFromJSONTyped,
    UserRequestToJSON,
} from './UserRequest';

/**
 *
 * @export
 * @interface PatchedBillRequest
 */
export interface PatchedBillRequest {
    /**
     *
     * @type {UserRequest}
     * @memberof PatchedBillRequest
     */
    author?: UserRequest;
    /**
     *
     * @type {string}
     * @memberof PatchedBillRequest
     */
    status?: string;
    /**
     *
     * @type {Date}
     * @memberof PatchedBillRequest
     */
    statusChanged?: Date;
    /**
     *
     * @type {string}
     * @memberof PatchedBillRequest
     */
    name?: string;
    /**
     *
     * @type {string}
     * @memberof PatchedBillRequest
     */
    description?: string;
}

/**
 * Check if a given object implements the PatchedBillRequest interface.
 */
export function instanceOfPatchedBillRequest(value: object): boolean {
    let isInstance = true;

    return isInstance;
}

export function PatchedBillRequestFromJSON(json: any): PatchedBillRequest {
    return PatchedBillRequestFromJSONTyped(json, false);
}

export function PatchedBillRequestFromJSONTyped(json: any, ignoreDiscriminator: boolean): PatchedBillRequest {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {

        'author': !exists(json, 'author') ? undefined : UserRequestFromJSON(json['author']),
        'status': !exists(json, 'status') ? undefined : json['status'],
        'statusChanged': !exists(json, 'status_changed') ? undefined : (new Date(json['status_changed'])),
        'name': !exists(json, 'name') ? undefined : json['name'],
        'description': !exists(json, 'description') ? undefined : json['description'],
    };
}

export function PatchedBillRequestToJSON(value?: PatchedBillRequest | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {

        'author': UserRequestToJSON(value.author),
        'status': value.status,
        'status_changed': value.statusChanged === undefined ? undefined : (value.statusChanged.toISOString()),
        'name': value.name,
        'description': value.description,
    };
}