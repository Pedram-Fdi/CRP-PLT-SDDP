from __future__ import absolute_import, division, print_function
import itertools as itools
import pandas as pd
from Constants import Constants

class Tool:
   
    #Append a list to another one only if the list to appebd is not empty
    @staticmethod
    def AppendIfNotEmpty( List1, List2):
        #if Constants.Debug: print("\n We are in 'Tool' Class -- AppendIfNotEmpty")
        if len( List2 ) > 0:
            List1.append( List2 )   

    @staticmethod
    def Transform2d(array, dimension1, dimension2):
        if len(array) != dimension1 * dimension2:
            raise ValueError("Array size does not match the specified dimensions.")
        result = [[array[i * dimension2 + j] 
                        for j in range(dimension2)] 
                            for i in range(dimension1)]
        return result
        
    #This function transform the sheet given in arguments into a dataframe
    @staticmethod
    def Transform3d(array, dimension1, dimension2, dimension3):
        if len(array) != dimension1 * dimension2 * dimension3:
            raise ValueError("Array size does not match the specified dimensions.")

        result = [[[
            array[i * (dimension2 * dimension3) + j * dimension3 + k]
                for k in range(dimension3)]
                    for j in range(dimension2)]
                        for i in range(dimension1)]

        return result
       
    @staticmethod
    def Transform4d(array, dimension1, dimension2, dimension3, dimension4):
        if len(array) != dimension1 * dimension2 * dimension3 * dimension4:
            raise ValueError("Array size does not match the specified dimensions.")
        
        result = [[[
            [array[i * (dimension2 * dimension3 * dimension4) + j * (dimension3 * dimension4) + k * dimension4 + l]
                for l in range(dimension4)]
                    for k in range(dimension3)]
                        for j in range(dimension2)]
                            for i in range(dimension1)]
        
        return result
    
    @staticmethod
    def Transform5d(array, dimension1, dimension2, dimension3, dimension4, dimension5):
        if len(array) != dimension1 * dimension2 * dimension3 * dimension4 * dimension5:
            raise ValueError("Array size does not match the specified dimensions.")

        result = [[[[[array[i * (dimension2 * dimension3 * dimension4 * dimension5) + 
                                  j * (dimension3 * dimension4 * dimension5) + 
                                  k * (dimension4 * dimension5) + 
                                  l * dimension5 + 
                                  m]
                    for m in range(dimension5)]
                    for l in range(dimension4)]
                    for k in range(dimension3)]
                    for j in range(dimension2)]
                    for i in range(dimension1)]
        return result
        
    @staticmethod
    def Transform6d(array, dimension1, dimension2, dimension3, dimension4, dimension5, dimension6):
        if len(array) != dimension1 * dimension2 * dimension3 * dimension4 * dimension5 * dimension6:
            raise ValueError("Array size does not match the specified dimensions.")

        result = [[[[[[array[i * (dimension2 * dimension3 * dimension4 * dimension5 * dimension6) + 
                                      j * (dimension3 * dimension4 * dimension5 * dimension6) + 
                                      k * (dimension4 * dimension5 * dimension6) + 
                                      l * (dimension5 * dimension6) + 
                                      m * dimension6 + 
                                      n]
                        for n in range(dimension6)]
                        for m in range(dimension5)]
                        for l in range(dimension4)]
                        for k in range(dimension3)]
                        for j in range(dimension2)]
                        for i in range(dimension1)]
        return result

    @staticmethod
    def Transform7d(array, dimension1, dimension2, dimension3, dimension4, dimension5, dimension6, dimension7):
        if len(array) != dimension1 * dimension2 * dimension3 * dimension4 * dimension5 * dimension6 * dimension7:
            raise ValueError("Array size does not match the specified dimensions.")

        result = [[[[[[[array[i * (dimension2 * dimension3 * dimension4 * dimension5 * dimension6 * dimension7) + 
                                       j * (dimension3 * dimension4 * dimension5 * dimension6 * dimension7) + 
                                       k * (dimension4 * dimension5 * dimension6 * dimension7) + 
                                       l * (dimension5 * dimension6 * dimension7) + 
                                       m * (dimension6 * dimension7) + 
                                       n * dimension7 + 
                                       o]
                         for o in range(dimension7)]
                         for n in range(dimension6)]
                         for m in range(dimension5)]
                         for l in range(dimension4)]
                         for k in range(dimension3)]
                         for j in range(dimension2)]
                         for i in range(dimension1)]
        return result
            
    @staticmethod
    def Print_Sparse_3D_Matrix(matrix):
        non_zero_entries = []
        for i, dim1 in enumerate(matrix):
            for j, dim2 in enumerate(dim1):
                for k, value in enumerate(dim2):
                    if value != 0:
                        non_zero_entries.append(f"({i}, {j+1}, {k}) = {value}") # {j+1} becuase our time t started from 1 not 0
        return "\n".join(non_zero_entries)

    @staticmethod
    def Print_Sparse_4D_Matrix(matrix):
        non_zero_entries = []
        for i, dim1 in enumerate(matrix):
            for j, dim2 in enumerate(dim1):
                for k, dim3 in enumerate(dim2):
                    for l, value in enumerate(dim3):
                        if value != 0:
                            non_zero_entries.append(f"({i}, {j+1}, {k}, {l}) = {value}") # {j+1} becuase our time t started from 1 not 0
        return "\n".join(non_zero_entries)
    
    # Define a recursive function to flatten nested lists
    @staticmethod
    def flatten(nested_list):
        for item in nested_list:
            if isinstance(item, list):
                yield from Tool.flatten(item)  
            else:
                yield item 