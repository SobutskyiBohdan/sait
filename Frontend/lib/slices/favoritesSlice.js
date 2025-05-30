import { createSlice } from "@reduxjs/toolkit"

const initialState = {
  favoriteIds: [],
  isLoaded: false,
}

const favoritesSlice = createSlice({
  name: "favorites",
  initialState,
  reducers: {
    addToFavorites: (state, action) => {
      const bookId = typeof action.payload === "object" ? action.payload.id : action.payload
      if (!state.favoriteIds.includes(bookId)) {
        state.favoriteIds.push(bookId)
      }
    },
    removeFromFavorites: (state, action) => {
      const bookId = typeof action.payload === "object" ? action.payload.id : action.payload
      state.favoriteIds = state.favoriteIds.filter((id) => id !== bookId)
    },
    setFavorites: (state, action) => {
      // action.payload може бути масивом ID або масивом об'єктів книжок
      if (Array.isArray(action.payload)) {
        state.favoriteIds = action.payload.map((item) => (typeof item === "object" ? item.id : item))
      } else {
        state.favoriteIds = []
      }
      state.isLoaded = true
    },
    clearFavorites: (state) => {
      state.favoriteIds = []
      state.isLoaded = false
    },
  },
})

export const { addToFavorites, removeFromFavorites, setFavorites, clearFavorites } = favoritesSlice.actions
export default favoritesSlice.reducer
