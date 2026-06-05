import { useQuery, useMutation } from '@tanstack/react-query'
import api, { endpoints } from '../../services/api'

interface Product {
  id: string
  name: string
  category: string
  price: number
  stock: number
  sku: string
  description?: string
}

interface ProductsParams {
  search?: string
  category?: string
  page?: number
  limit?: number
}

export function useProducts(params?: ProductsParams) {
  return useQuery({
    queryKey: ['products', params],
    queryFn: async () => {
      const { data } = await api.get<Product[]>(endpoints.products, { params })
      return data
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

export function useProduct(id: string) {
  return useQuery({
    queryKey: ['product', id],
    queryFn: async () => {
      const { data } = await api.get<Product>(endpoints.product(id))
      return data
    },
  })
}

export function useCreateProduct() {
  return useMutation({
    mutationFn: async (product: Omit<Product, 'id'>) => {
      const { data } = await api.post<Product>(endpoints.products, product)
      return data
    },
  })
}

export function useUpdateProduct() {
  return useMutation({
    mutationFn: async ({ id, ...product }: Product) => {
      const { data } = await api.put<Product>(endpoints.product(id), product)
      return data
    },
  })
}

export function useDeleteProduct() {
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(endpoints.product(id))
    },
  })
}
