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


import * as runtime from '../runtime';
import type {
  Bill,
  BillRequest,
  PatchedBillRequest,
  VoteCounts,
  VoteRequest,
} from '../models/index';
import {
    BillFromJSON,
    BillToJSON,
    BillRequestFromJSON,
    BillRequestToJSON,
    PatchedBillRequestFromJSON,
    PatchedBillRequestToJSON,
    VoteCountsFromJSON,
    VoteCountsToJSON,
    VoteRequestFromJSON,
    VoteRequestToJSON,
} from '../models/index';

export interface BillsPartialUpdateRequest {
    id: number;
    patchedBillRequest?: PatchedBillRequest;
}

export interface BillsRetrieveRequest {
    id: number;
}

export interface BillsUpdateRequest {
    id: number;
    billRequest: BillRequest;
}

export interface BillsVoteCreateRequest {
    id: number;
    voteRequest: VoteRequest;
}

/**
 *
 */
export class BillsApi extends runtime.BaseAPI {

    /**
     */
    async billsListRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<Array<Bill>>> {
        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = await this.configuration.apiKey("Authorization"); // tokenAuth authentication
        }

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("jwtAuth", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/bills/`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => jsonValue.map(BillFromJSON));
    }

    /**
     */
    async billsList(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<Array<Bill>> {
        const response = await this.billsListRaw(initOverrides);
        return await response.value();
    }

    /**
     */
    async billsPartialUpdateRaw(requestParameters: BillsPartialUpdateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<Bill>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling billsPartialUpdate.');
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = await this.configuration.apiKey("Authorization"); // tokenAuth authentication
        }

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("jwtAuth", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/bills/{id}/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'PATCH',
            headers: headerParameters,
            query: queryParameters,
            body: PatchedBillRequestToJSON(requestParameters.patchedBillRequest),
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => BillFromJSON(jsonValue));
    }

    /**
     */
    async billsPartialUpdate(requestParameters: BillsPartialUpdateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<Bill> {
        const response = await this.billsPartialUpdateRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     */
    async billsRetrieveRaw(requestParameters: BillsRetrieveRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<Bill>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling billsRetrieve.');
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = await this.configuration.apiKey("Authorization"); // tokenAuth authentication
        }

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("jwtAuth", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/bills/{id}/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => BillFromJSON(jsonValue));
    }

    /**
     */
    async billsRetrieve(requestParameters: BillsRetrieveRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<Bill> {
        const response = await this.billsRetrieveRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     */
    async billsUpdateRaw(requestParameters: BillsUpdateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<Bill>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling billsUpdate.');
        }

        if (requestParameters.billRequest === null || requestParameters.billRequest === undefined) {
            throw new runtime.RequiredError('billRequest','Required parameter requestParameters.billRequest was null or undefined when calling billsUpdate.');
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = await this.configuration.apiKey("Authorization"); // tokenAuth authentication
        }

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("jwtAuth", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/bills/{id}/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'PUT',
            headers: headerParameters,
            query: queryParameters,
            body: BillRequestToJSON(requestParameters.billRequest),
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => BillFromJSON(jsonValue));
    }

    /**
     */
    async billsUpdate(requestParameters: BillsUpdateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<Bill> {
        const response = await this.billsUpdateRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     */
    async billsVoteCreateRaw(requestParameters: BillsVoteCreateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<VoteCounts>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling billsVoteCreate.');
        }

        if (requestParameters.voteRequest === null || requestParameters.voteRequest === undefined) {
            throw new runtime.RequiredError('voteRequest','Required parameter requestParameters.voteRequest was null or undefined when calling billsVoteCreate.');
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = await this.configuration.apiKey("Authorization"); // tokenAuth authentication
        }

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("jwtAuth", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/bills/{id}/vote/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: VoteRequestToJSON(requestParameters.voteRequest),
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => VoteCountsFromJSON(jsonValue));
    }

    /**
     */
    async billsVoteCreate(requestParameters: BillsVoteCreateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<VoteCounts> {
        const response = await this.billsVoteCreateRaw(requestParameters, initOverrides);
        return await response.value();
    }

}
