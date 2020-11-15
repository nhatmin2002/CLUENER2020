import torch
import torch.nn as nn
from torch import optim

import config
from model import BiLSTM_CRF
from data_process import Processor
from Vocabulary import Vocabulary
from dev_split import dev_split
from data_loader import NERDataset
from torch.utils.data import DataLoader
from train import train, test, sample_test

input_array = [[1642, 1291, 40, 2255, 970, 46, 124, 1604, 1915, 547, 0, 173,
                303, 124, 1029, 52, 20, 2839, 2, 2255, 2078, 1553, 225, 540,
                96, 469, 1704, 0, 174, 3, 8, 728, 903, 403, 538, 668,
                179, 27, 78, 292, 7, 134, 2078, 1029, 0, 0, 0, 0,
                0],
               [28, 6, 926, 72, 209, 330, 308, 167, 87, 1345, 1, 528,
                412, 0, 584, 1, 6, 28, 326, 1, 361, 342, 3256, 17,
                19, 1549, 3257, 131, 2, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                0],
               [6, 3, 58, 1930, 37, 407, 1068, 40, 1299, 1443, 103, 1235,
                1040, 139, 879, 11, 124, 200, 135, 97, 1138, 1016, 402, 696,
                337, 215, 402, 288, 10, 5, 5, 17, 0, 248, 597, 110,
                84, 1, 135, 97, 1138, 1016, 402, 696, 402, 200, 109, 164,
                0],
               [174, 6, 110, 84, 3, 477, 332, 133, 66, 11, 557, 107,
                181, 350, 0, 70, 196, 166, 50, 120, 26, 89, 66, 19,
                564, 0, 36, 26, 48, 243, 1308, 0, 139, 212, 621, 300,
                0, 444, 720, 4, 177, 165, 164, 2, 0, 0, 0, 0,
                0]]

label_array = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 14, 14, 14, 14, 14,
                14, 14, 14, 14, 14, 0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 4, 14, 14, 14, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 1, 11, 0, 1, 11, 11, 11, 11, 11, 0, 0, 0, 0, 8, 18, 18,
                18, 18, 18, 18, 18, 18, 0, 0, 9, 19, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 8, 18, 18, 18, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 18, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]

test_input = torch.tensor(input_array, dtype=torch.long)
test_label = torch.tensor(label_array, dtype=torch.long)


def run():
    # 设置gpu为命令行参数指定的id
    if config.gpu != '':
        device = torch.device(f"cuda:{config.gpu}")
    else:
        device = torch.device("cpu")
    # 处理数据，分离文本和标签
    processor = Processor(config)
    processor.data_process()
    # 建立词表
    vocab = Vocabulary(config)
    vocab.get_vocab()
    # 分离出验证集
    word_train, word_dev, label_train, label_dev = dev_split(config.train_dir)
    # build dataset
    train_dataset = NERDataset(word_train, label_train, vocab, config.label2id)
    dev_dataset = NERDataset(word_dev, label_dev, vocab, config.label2id)
    # build data_loader
    train_loader = DataLoader(train_dataset, batch_size=config.batch_size,
                              shuffle=True, collate_fn=train_dataset.collate_fn)
    dev_loader = DataLoader(dev_dataset, batch_size=config.batch_size,
                            shuffle=True, collate_fn=dev_dataset.collate_fn)
    # model
    model = BiLSTM_CRF(embedding_size=config.embedding_size,
                       hidden_size=config.hidden_size,
                       drop_out=config.drop_out,
                       vocab_size=vocab.vocab_size(),
                       tagset_size=vocab.label_size())
    model.to(device)
    # loss and optimizer
    loss_function = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=config.lr, betas=config.betas)
    with torch.no_grad():
        sample_test(test_input, test_label, model, device)
    # train and test
    train(train_loader, dev_loader, vocab, model, loss_function, optimizer, device)
    with torch.no_grad():
        # test on the final test set
        test(config.test_dir, vocab, model, loss_function, device)
        sample_test(test_input, test_label, model, device)


if __name__ == '__main__':
    run()