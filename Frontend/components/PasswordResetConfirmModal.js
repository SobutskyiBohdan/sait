'use client';

import React from 'react';

export default function PasswordResetConfirmModal({ isOpen, onClose, email }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-sm w-full shadow-lg">
        <h2 className="text-xl font-bold mb-4">Password Reset Email Sent</h2>
        <p className="mb-4">
          We have sent a password reset link to <strong>{email}</strong>. Please check your inbox.
        </p>
        <button
          onClick={onClose}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Close
        </button>
      </div>
    </div>
  );
}