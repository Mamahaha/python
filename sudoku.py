#!/usr/bin/python
import math
import copy
import time

class sudoku_parser:
  '''sudoku parser
  '''
  __INIT_VALUE = 0
  __DELIMITER = ','
  __matrix_width = 9
  __block_width = 3

  ori_matrix = None
  empty_cells = []
  
  def __init__(self):
    print 'Starting SUDOKU parser'
  
  def init_matrix(self, file_path):
    #Read file
    lines = []
    try:
      fh = open(file_path)
      lines = fh.readlines()
      fh.close()
    except Exception, ex:
      print '[ERROR] Open matrix file failed:', file_path
      return False
    
    #Init matrix width
    line_count = len(lines)
    self.__matrix_width = line_count 
    if (line_count % int(math.sqrt(line_count)) != 0):
      print '[ERROR] Matrix width %d is wrong' %line_count
      return False
    self.__block_width = int(math.sqrt(line_count))      
    
    w = self.__matrix_width
    sw = self.__block_width
    self.ori_matrix = [[self.__INIT_VALUE for i in range(w)] for j in range(w)]

    #Fill matrix
    line_count = 0
    for line in lines:    
      if not self.__fill_line(line, line_count):
        return False
      line_count += 1
    
    self.empty_cells = [(i,j) for i in range(w) for j in range(w) if self.ori_matrix[i][j] == self.__INIT_VALUE]
    self.print_matrix(self.ori_matrix)
    return True

  def __fill_line(self, line, line_count):
    w = self.__matrix_width
    sub_lines = line.strip().split(self.__DELIMITER)
    if len(sub_lines) != w:
      print '[ERROR] The item count in line <%s> is wrong' %line
      return False
    
    item_count = 0
    for item in sub_lines:
      new_item = -1
      try:
        new_item = int(item.strip())
      except Exception, ex:
        print '[ERROR] The value of item <%s> is wrong' %item
        return False
      if new_item < self.__INIT_VALUE or new_item > self.__INIT_VALUE + w:
        print '[ERROR] The value of item <%s> is out of bound' %item
        return False
      self.ori_matrix[line_count][item_count] = new_item
      item_count += 1
    return True
    
  def print_matrix(self, matrix):
    print ('|-' + '-' * self.__block_width * 2) * (self.__matrix_width / self.__block_width) + '|'
    for i in range(self.__matrix_width):
      print '|',
      for j in range(self.__matrix_width):
        print matrix[i][j],
        if (j + 1) % self.__block_width == 0:
          print '|',
      print ''
      if (i + 1) % self.__block_width == 0:
        print ('|-' + '-' * self.__block_width * 2) * (self.__matrix_width / self.__block_width) + '|'
  
  def fill_matrix(self, n, matrix):
    w = self.__matrix_width
    if n >= len(self.empty_cells):
      print '\n=====Full matrix========'
      self.print_matrix(matrix)
      return True

    (i, j) = self.empty_cells[n]
    found_flag = False
    cur_matrix = copy.deepcopy(matrix)
    for k in range(1, w + 1):
      if self.__validate_line(i, j, k, cur_matrix):
        cur_matrix[i][j] = k
        if self.fill_matrix(n + 1, cur_matrix):
          found_flag = True
          break
    if not found_flag:
      return False
    matrix = cur_matrix
    return True
   
  def __validate_line(self, m_i, n_i, value, matrix):
    if matrix[m_i][n_i] == value:
      return True
    w = self.__matrix_width
    sw = self.__block_width
    flip_line = [matrix[i][n_i] for i in range(w)]
    block_line = [matrix[i][j] for i in range(m_i/sw*sw, m_i/sw*sw+sw) for j in range(n_i/sw*sw, n_i/sw*sw+sw)]

    if value in matrix[m_i] or value in flip_line or value in block_line:
      return False    
    return True

if __name__ == '__main__':
  pp = sudoku_parser()
  if pp.init_matrix('sudoku.txt'):
    if pp.fill_matrix(0, pp.ori_matrix):
      print '\nGot it!!'
    else:
      print 'No matched matrix exists'
    print 'End of filling matrix'
