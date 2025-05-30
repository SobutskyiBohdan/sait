import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react"
import { getAuthToken } from "../utils/cookies"

export const booksApi = createApi({
  reducerPath: "booksApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000",
    prepareHeaders: (headers, { getState }) => {
      // Спочатку пробуємо отримати токен з Redux
      let token = getState().auth.token

      // Якщо в Redux немає токена, пробуємо з cookies
      if (!token) {
        token = getAuthToken()
      }

      if (token) {
        headers.set("authorization", `Bearer ${token}`)
      }

      headers.set("Content-Type", "application/json")
      headers.set("Accept", "application/json")
      return headers
    },
    mode: "cors",
    credentials: "include",
    timeout: 15000,
  }),
  tagTypes: ["Book", "Favorites"],
  endpoints: (builder) => ({
    getBooks: builder.query({
      query: (params) => {
        const requestConfig = {
          url: "/scraping/book_list/",
          params: {
            ...params,
            limit: Math.min(params?.limit || 20, 20), // Максимум 20 книжок на сторінку
            ...(params?.title && { title: params.title }),
            ...(params?.genre && { genre: params.genre }),
            ...(params?.fromYear && { fromYear: params.fromYear }),
            ...(params?.toYear && { toYear: params.toYear }),
          },
        }

        if (process.env.NODE_ENV === "development") {
          console.log("📚 Books API Request:", requestConfig)
          console.log("🌐 Full URL:", `${process.env.NEXT_PUBLIC_API_URL}/scraping/book_list/`)
        }

        return requestConfig
      },
      transformResponse: (response, meta, arg) => {
        console.log("📚 Books API Response:", response)

        if (response && typeof response === "object" && response.results) {
          return {
            books: response.results || [],
            total: response.count || 0,
            page: arg?.page || 1,
            limit: Math.min(arg?.limit || 20, 20),
          }
        }

        if (Array.isArray(response)) {
          return {
            books: response,
            total: response.length,
            page: arg?.page || 1,
            limit: Math.min(arg?.limit || 20, 20),
          }
        }

        return {
          books: response?.books || response || [],
          total: response?.total || response?.count || 0,
          page: arg?.page || 1,
          limit: Math.min(arg?.limit || 20, 20),
        }
      },
      transformErrorResponse: (response, meta, arg) => {
        console.error("🚨 Books API Error:", response)
        return response
      },
      providesTags: ["Book"],
    }),
    getBookById: builder.query({
      query: (id) => `/scraping/book_detail/${id}/`,
      providesTags: (result, error, id) => [{ type: "Book", id }],
    }),
    getRecommendedBooks: builder.query({
      query: (bookId) => `/scraping/book_detail/${bookId}/recommended/`,
      providesTags: ["Book"],
    }),
    // Admin endpoints
    createBook: builder.mutation({
      query: (bookData) => ({
        url: "/scraping/book_create/",
        method: "POST",
        body: bookData,
      }),
      invalidatesTags: ["Book"],
    }),
    updateBook: builder.mutation({
      query: ({ id, ...bookData }) => ({
        url: `/scraping/book_update/${id}/`,
        method: "PUT",
        body: bookData,
      }),
      invalidatesTags: ["Book"],
    }),
    deleteBook: builder.mutation({
      query: (id) => ({
        url: `/scraping/book_delete/${id}/`,
        method: "DELETE",
      }),
      invalidatesTags: ["Book"],
    }),
    // Favorites endpoints
    getFavorites: builder.query({
      query: () => "/scraping/book_favorites/",
      providesTags: ["Favorites"],
      transformResponse: (response) => {
        console.log("❤️ Favorites API Response:", response)
        // Якщо response це масив книжок
        if (Array.isArray(response)) {
          return response
        }
        // Якщо response це об'єкт з results
        if (response && response.results) {
          return response.results
        }
        // Якщо response це об'єкт з books
        if (response && response.books) {
          return response.books
        }
        return []
      },
      transformErrorResponse: (response) => {
        console.error("❌ Get Favorites API Error:", response)
        return response
      },
    }),
    addToFavorites: builder.mutation({
      query: (bookId) => {
        console.log("❤️ Adding to favorites, bookId:", bookId)
        return {
          url: `/scraping/book_favorites_add/`,
          method: "POST",
          body: {
            book_id: Number.parseInt(bookId, 10), // Переконуємось що це число
          },
        }
      },
      invalidatesTags: ["Favorites"],
      transformErrorResponse: (response) => {
        console.error("❌ Add to Favorites API Error:", response)
        return response
      },
    }),
    removeFromFavorites: builder.mutation({
      query: (bookId) => {
        console.log("💔 Removing from favorites, bookId:", bookId)
        return {
          url: `/scraping/book_favorites_remove/`,
          method: "POST",
          body: {
            book_id: Number.parseInt(bookId, 10), // Переконуємось що це число
          },
        }
      },
      invalidatesTags: ["Favorites"],
      transformErrorResponse: (response) => {
        console.error("❌ Remove from Favorites API Error:", response)
        return response
      },
    }),
  }),
})

export const {
  useGetBooksQuery,
  useGetBookByIdQuery,
  useGetRecommendedBooksQuery,
  useCreateBookMutation,
  useUpdateBookMutation,
  useDeleteBookMutation,
  useGetFavoritesQuery,
  useAddToFavoritesMutation,
  useRemoveFromFavoritesMutation,
} = booksApi
