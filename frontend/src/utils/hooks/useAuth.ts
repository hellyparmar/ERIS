import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api, { endpoints } from '../../services/api'

interface User {
  id: string
  email: string
  name: string
  role: string
}

export function useAuth() {
  const queryClient = useQueryClient()

  const { data: user, isLoading, error } = useQuery({
    queryKey: ['auth', 'user'],
    queryFn: async () => {
      const { data } = await api.get<User>(endpoints.me)
      return data
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })

  const loginMutation = useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      const { data } = await api.post<{ token: string; user: User }>(
        endpoints.login,
        credentials
      )
      localStorage.setItem('token', data.token)
      return data
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['auth', 'user'], data.user)
    },
  })

  const logout = () => {
    localStorage.removeItem('token')
    queryClient.setQueryData(['auth', 'user'], null)
  }

  return {
    user,
    isLoading,
    error,
    login: loginMutation.mutate,
    isAuthenticating: loginMutation.isPending,
    logout,
    isAuthenticated: !!user,
  }
}
