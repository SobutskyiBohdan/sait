"use client"

import { useState, useEffect } from "react"
import { User, Edit3, Heart, Download, X } from "lucide-react"
import toast from "react-hot-toast"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useGetProfileQuery, useUpdateProfileMutation } from "@/lib/api/authApi"
import { useGetFavoritesQuery, useRemoveFromFavoritesMutation } from "@/lib/api/booksApi"
import { useAppSelector, useAppDispatch } from "@/lib/hooks"
import { removeFromFavorites, setFavorites } from "@/lib/slices/favoritesSlice"
import Breadcrumb from "@/components/breadcrumb"

export default function ProfilePage() {
  const [isEditing, setIsEditing] = useState(false)
  const { data: profile } = useGetProfileQuery()
  const { data: favorites, isLoading: favoritesLoading } = useGetFavoritesQuery()
  const [removeFromFavoritesMutation] = useRemoveFromFavoritesMutation()
  const dispatch = useAppDispatch()
  const { isAuthenticated } = useAppSelector((state) => state.auth)
  const router = useRouter()

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/")
    }
  }, [isAuthenticated, router])

  // Update favorites in Redux when data loads
  useEffect(() => {
    if (favorites && Array.isArray(favorites)) {
      const favoriteIds = favorites.map((book) => book.id)
      dispatch(setFavorites(favoriteIds))
    }
  }, [favorites, dispatch])

  const handleRemoveFromFavorites = async (bookId, bookTitle) => {
    try {
      await removeFromFavoritesMutation(bookId).unwrap()
      dispatch(removeFromFavorites(bookId))
      toast.success(`"${bookTitle}" removed from favorites`)
    } catch (error) {
      console.error("Error removing from favorites:", error)
      toast.error("Failed to remove from favorites")
    }
  }

  if (!isAuthenticated) {
    return null
  }

  if (isEditing) {
    return <EditProfileForm onCancel={() => setIsEditing(false)} />
  }

  return (
    <div className="px-6 py-12">
      <div className="max-w-7xl mx-auto">
        <Breadcrumb items={[{ label: "Home", href: "/" }, { label: "Profile" }]} />

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
          {/* Profile Section */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-xl p-8 animate-slide-in">
              <h1 className="text-3xl font-bold text-black mb-8 text-center">Profile</h1>

              <div className="bg-gradient-to-br from-gray-200 to-gray-400 w-48 h-48 rounded-2xl flex items-center justify-center mb-8 mx-auto shadow-lg">
                <User className="w-24 h-24 text-white" />
              </div>

              <div className="space-y-6 mb-8">
                <div>
                  <label className="block text-brown-secondary font-semibold mb-2">Username</label>
                  <div className="bg-gray-50 rounded-lg p-3 text-black font-medium">
                    {profile?.username || "Username"}
                  </div>
                </div>
                <div>
                  <label className="block text-brown-secondary font-semibold mb-2">Email</label>
                  <div className="bg-gray-50 rounded-lg p-3 text-black font-medium">{profile?.email || "Email"}</div>
                </div>
              </div>

              <div className="space-y-4">
                <button
                  onClick={() => setIsEditing(true)}
                  className="btn-primary text-white px-6 py-3 rounded-lg font-medium w-full flex items-center justify-center gap-2"
                >
                  <Edit3 className="w-5 h-5" />
                  Edit profile
                </button>

                <Link
                  href="/profile/export"
                  className="border-2 border-brown-secondary text-brown-secondary px-6 py-3 rounded-lg font-medium w-full flex items-center justify-center gap-2 hover:bg-brown-secondary hover:text-white transition-all duration-300"
                >
                  <Download className="w-5 h-5" />
                  Export Books
                </Link>
              </div>
            </div>
          </div>

          {/* Favorites Section */}
          <div className="lg:col-span-3">
            <div className="animate-fade-in">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-3xl font-bold text-black">Favorites</h2>
                {favorites && favorites.length > 0 && (
                  <span className="text-brown-secondary">
                    {favorites.length} book{favorites.length !== 1 ? "s" : ""}
                  </span>
                )}
              </div>

              {favoritesLoading ? (
                <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brown-primary mx-auto mb-4"></div>
                  <p className="text-brown-secondary">Loading favorites...</p>
                </div>
              ) : favorites && favorites.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {favorites.map((book, index) => (
                    <div
                      key={book.id}
                      className="animate-fade-in bg-white rounded-2xl shadow-lg overflow-hidden group relative"
                      style={{ animationDelay: `${index * 0.1}s` }}
                    >
                      {/* Remove button */}
                      <button
                        onClick={() => handleRemoveFromFavorites(book.id, book.title)}
                        className="absolute top-3 right-3 z-10 bg-white/90 backdrop-blur-sm p-2 rounded-full hover:bg-white transition-all duration-300 shadow-lg opacity-0 group-hover:opacity-100"
                      >
                        <X className="w-4 h-4 text-red-500" />
                      </button>

                      {/* Book Image */}
                      <div className="relative overflow-hidden">
                        <Link href={`/books/${book.id}`}>
                          <div className="aspect-[3/4] overflow-hidden">
                            <img
                              src={book.image || "/placeholder.svg?height=400&width=300"}
                              alt={book.title}
                              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                            />
                          </div>
                        </Link>
                      </div>

                      {/* Book Details */}
                      <div className="p-4">
                        <Link href={`/books/${book.id}`}>
                          <h3 className="font-bold text-lg mb-2 text-black hover:text-brown-primary transition-colors line-clamp-2 leading-tight">
                            {book.title}
                          </h3>
                        </Link>
                        <p className="text-sm mb-2 text-brown-secondary font-medium">{book.author}</p>
                        <p className="text-sm mb-3 text-brown-secondary">{book.year}</p>
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-xl text-brown-primary">{book.price}</span>
                          <button
                            onClick={() => handleRemoveFromFavorites(book.id, book.title)}
                            className="p-2 rounded-full hover:bg-red-50 transition-all duration-300"
                          >
                            <Heart className="w-5 h-5 fill-red-500 text-red-500" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
                  <Heart className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-xl font-bold text-black mb-2">No favorite books yet</h3>
                  <p className="text-gray-500 mb-6">Start exploring and add books to your favorites!</p>
                  <Link
                    href="/"
                    className="btn-primary text-white px-6 py-3 rounded-lg font-medium inline-flex items-center gap-2"
                  >
                    Browse Books
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function EditProfileForm({ onCancel }) {
  const [updateProfile, { isLoading }] = useUpdateProfileMutation()
  const { data: profile } = useGetProfileQuery()
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    currentPassword: "",
    newPassword: "",
  })

  useEffect(() => {
    if (profile) {
      setFormData((prev) => ({
        ...prev,
        username: profile.username || "",
        email: profile.email || "",
      }))
    }
  }, [profile])

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await updateProfile(formData).unwrap()
      toast.success("Profile updated successfully!")
      onCancel()
    } catch (error) {
      console.error("Profile update failed:", error)
      toast.error("Failed to update profile. Please try again.")
    }
  }

  return (
    <div className="px-6 py-12">
      <div className="max-w-7xl mx-auto">
        <Breadcrumb items={[{ label: "Home", href: "/" }, { label: "Profile" }]} />

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
          {/* Profile Edit Form */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-xl p-8 animate-slide-in">
              <h1 className="text-3xl font-bold text-black mb-8 text-center">Edit Profile</h1>

              <div className="bg-gradient-to-br from-gray-200 to-gray-400 w-48 h-48 rounded-2xl flex items-center justify-center mb-8 mx-auto shadow-lg">
                <User className="w-24 h-24 text-white" />
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label className="block text-brown-secondary font-semibold mb-2">Username</label>
                  <input
                    type="text"
                    placeholder="Enter username"
                    value={formData.username}
                    onChange={(e) => setFormData((prev) => ({ ...prev, username: e.target.value }))}
                    className="w-full border-2 border-brown-secondary rounded-lg px-4 py-3 bg-white search-input focus:outline-none focus:border-brown-primary"
                  />
                </div>
                <div>
                  <label className="block text-brown-secondary font-semibold mb-2">Email</label>
                  <input
                    type="email"
                    placeholder="example@gmail.com"
                    value={formData.email}
                    onChange={(e) => setFormData((prev) => ({ ...prev, email: e.target.value }))}
                    className="w-full border-2 border-brown-secondary rounded-lg px-4 py-3 bg-white search-input focus:outline-none focus:border-brown-primary"
                  />
                </div>
                <div>
                  <label className="block text-brown-secondary font-semibold mb-2">Current Password</label>
                  <input
                    type="password"
                    placeholder="Your current password"
                    value={formData.currentPassword}
                    onChange={(e) => setFormData((prev) => ({ ...prev, currentPassword: e.target.value }))}
                    className="w-full border-2 border-brown-secondary rounded-lg px-4 py-3 bg-white search-input focus:outline-none focus:border-brown-primary"
                  />
                </div>
                <div>
                  <label className="block text-brown-secondary font-semibold mb-2">New Password</label>
                  <input
                    type="password"
                    placeholder="New password"
                    value={formData.newPassword}
                    onChange={(e) => setFormData((prev) => ({ ...prev, newPassword: e.target.value }))}
                    className="w-full border-2 border-brown-secondary rounded-lg px-4 py-3 bg-white search-input focus:outline-none focus:border-brown-primary"
                  />
                </div>
                <button type="button" className="text-brown-secondary hover:text-brown-primary btn-secondary">
                  Forgot your password?
                </button>
                <div className="flex gap-4">
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="btn-primary text-white px-6 py-3 rounded-lg font-medium flex-1 disabled:opacity-50"
                  >
                    {isLoading ? "Saving..." : "Save"}
                  </button>
                  <button
                    type="button"
                    onClick={onCancel}
                    className="border-2 border-brown-secondary text-brown-secondary px-6 py-3 rounded-lg font-medium flex-1 hover:bg-brown-secondary hover:text-white transition-all duration-300"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* Favorites Section */}
          <div className="lg:col-span-3">
            <div className="animate-fade-in">
              <h2 className="text-3xl font-bold text-black mb-8">Favorites</h2>
              <div className="bg-white rounded-2xl shadow-lg p-8">
                <p className="text-gray-500 text-center">Your favorite books will appear here</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
