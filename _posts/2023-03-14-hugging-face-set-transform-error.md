---
layout: post
title: Training CLIP image KeyError when using HuggingFace set_transform
subtitle: on-the-fly transform error
tags: [code,HuggingFace]
comments: true
---

HuggingFace训练CLIP时，通过set_transform函数实现对batch进行image transformer。set_transform会在调用__getitem__的时候执行[1]，优点在于：
1. set_transform方法可以在训练时动态地应用变换，而不需要提前保存变换后的图像，这可以节省存储空间和计算时间；
2. 在一个batch上执行transform有一些优势，例如可以实现更复杂的数据增强方法，如mixup、cutmix等，这些方法需要在一个batch内部进行样本的混合或者裁剪；

[1]
> This function is applied right before returning the objects in __getitem__.
>
> Set getitem return format using this transform. The transform is applied on-the-fly on batches when getitem is called. 


```
def transform_images(examples):
    images = [read_image(image_file, mode=ImageReadMode.RGB) for image_file in examples[image_column]]
    examples["pixel_values"] = [image_transformations(image) for image in images]
    return examples

train_dataset.set_transform(transform_images)
```

结果运行training的时候报错：
```
 images = [read_image(image_file, mode=ImageReadMode.RGB) for image_file in examples[image_column]]
 KeyError: 'image'
```

打印出来发现image字段在training开始之前输入trainer的还是有的，传到transform_images函数中就没有了。

于是查看了下trainer.py的源码，发现实际是在获取epoch数据的时候执行image_transformer，在此之前的data_loader里面有个_remove_unused_columns函数，会将不需要的columns删除，image字段就是在这一步被删除了。

```
# 删除不需要字段
def _remove_unused_columns(self, dataset: "datasets.Dataset", description: Optional[str] = None):
    if not self.args.remove_unused_columns:
        return dataset
    self._set_signature_columns_if_needed()
    signature_columns = self._signature_columns

    ignored_columns = list(set(dataset.column_names) - set(signature_columns))
    ...

def get_train_dataloader(self) -> DataLoader:
    ...
    if is_datasets_available() and isinstance(train_dataset, datasets.Dataset):
            train_dataset = self._remove_unused_columns(train_dataset, description="training")
    ...

...

# 执行image transformer
for step, inputs in enumerate(epoch_iterator):
...

```
于是将控制是否删除unused columns的配置remove_unused_columns设置为false，但是这样的话多余的字段就会传入模型前向传播而报错，于是在collate_fn函数中仅保留需要训练的字段。
```
def collate_fn(examples):
    pixel_values = torch.stack([example["pixel_values"] for example in examples])
    input_ids = torch.tensor([example["input_ids"] for example in examples], dtype=torch.long)
    attention_mask = torch.tensor([example["attention_mask"] for example in examples], dtype=torch.long)
    return {
        "pixel_values": pixel_values,
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "return_loss": True,
    }
```