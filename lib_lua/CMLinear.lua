--[[ Description: CLinear class implements linear GNN module with multiplicative terms.
]]

CMLinear = torch.class('CMLinear')

function CMLinear:__init(nInputs, taMins, taMaxs)
  self.taMins = taMins
  self.taMaxs = taMaxs

  self.nInputs = nInputs
  self.nMulTerms = (nInputs * (nInputs-1))/2
  self.teTheta = torch.zeros(1, self.nInputs + self.nMulTerms + 1)
  self.teGradTheta = torch.zeros(self.teTheta:size())
end

function CMLinear:pri_extendWithMulTerms(teInput)
  local nD = teInput:size(2)
  if nD < 2 then
    return teInput
  end

  -- 1) Build matrix of for all pairs of input multiplies
  local teMulTerms = torch.zeros(teInput:size(1), self.nMulTerms)
  local idMul = 0
  for i=1,nD do
    for j=i+1,nD do
      idMul = idMul + 1
      teMulTerms:select(2, idMul):copy(torch.cmul(teInput:select(2, i), teInput:select(2, j)))
    end
  end

  -- 2) Extend
  return torch.cat({teInput, teMulTerms}, 2)
end

function CMLinear:predict(teInput)
  local teInputExtended = self:pri_extendWithMulTerms(teInput)
  local teV1 = torch.Tensor(teInputExtended:size(1), 1):fill(self.teTheta[1][1]) -- bias
  local teV2 = self.teTheta:narrow(2, 2, self.teTheta:size(2)-1):t()
  local teOutput = torch.addmm(teV1, teInputExtended, teV2)
  teOutput:clamp(self.taMins.output, self.taMaxs.output)

  return teOutput
end

function CMLinear:train(teInput, teTarget)
  local teInputExtended = self:pri_extendWithMulTerms(teInput)
  local teA = torch.cat(torch.ones(teInputExtended:size(1), 1), teInputExtended)
  local teB = teTarget

  local teX
  function fuWrapGels()
    teX = torch.gels(teB, teA)
  end

  if pcall(fuWrapGels) then
     self.teTheta:copy(teX)
  else
     print("Error in gels call!!")
     self.teTheta:fill(0)
     self.teTheta[1][1] = torch.mean(teTarget)
  end
end

function CMLinear:getParamPointer()
  return self.teTheta
end

function CMLinear:getGradParamPointer()
  return self.teGradTheta
end
