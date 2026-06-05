import { useQuery, useMutation } from '@tanstack/react-query'
import api, { endpoints } from '../../services/api'

interface Sale {
  id: string
  date: string
  outlet: string
  customer?: string
  amount: number
  items: number
  paymentMethod: string
}

interface SalesParams {
  outlet?: string
  startDate?: string
  endDate?: string
  page?: number
  limit?: number
}

export function useSales(params?: SalesParams) {
  return useQuery({
    queryKey: ['sales', params],
    queryFn: async () => {
      const { data } = await api.get<Sale[]>(endpoints.sales, { params })
      return data
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
  })
}

export function useSale(id: string) {
  return useQuery({
    queryKey: ['sale', id],
    queryFn: async () => {
      const { data } = await api.get<Sale>(endpoints.sale(id))
      return data
    },
  })
}

export function useCreateSale() {
  return useMutation({
    mutationFn: async (sale: Omit<Sale, 'id'>) => {
      const { data } = await api.post<Sale>(endpoints.sales, sale)
      return data
    },
  })
}
